/*
Copyright 2016 EPAM Systems, Inc.

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

    http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
*/
package com.epam.dlab.process.builder;

import com.aegisql.conveyor.Expireable;
import com.aegisql.conveyor.Testing;
import com.aegisql.conveyor.TimeoutAction;
import com.epam.dlab.process.model.DlabProcess;
import com.epam.dlab.process.model.ProcessData;
import com.epam.dlab.process.model.ProcessInfo;
import com.epam.dlab.process.model.ProcessStatus;
import lombok.extern.slf4j.Slf4j;

import java.io.BufferedReader;
import java.io.IOException;
import java.io.InputStream;
import java.io.InputStreamReader;
import java.lang.reflect.Field;
import java.util.Collection;
import java.util.LinkedList;
import java.util.concurrent.CompletableFuture;
import java.util.function.Function;
import java.util.function.Supplier;

import static com.epam.dlab.process.model.ProcessStatus.*;

@Slf4j
public class ProcessInfoBuilder implements Supplier<ProcessInfo>, Testing, TimeoutAction, Expireable {

	private final ProcessData processData;
	private final long startTimeStamp = System.currentTimeMillis();
	private ProcessStatus status = CREATED;
	private final StringBuilder stdOut = new StringBuilder();
	private final StringBuilder stdErr = new StringBuilder();
	private int exitCode = -1;
	private String[] command = new String[]{"N/A"};
	private Collection<ProcessInfo> rejected = null;
	private int pid = -1;

	private boolean finished = false;
	private boolean stdOutClosed = false;
	private boolean stdErrClosed = false;

	private Process p = null;
	private CompletableFuture<ProcessInfo> future;
	private long expirationTime;

	public ProcessInfoBuilder(ProcessData processData, long ttl) {
		this.processData = processData;
		this.expirationTime = System.currentTimeMillis() + ttl;
	}

	public static void schedule(ProcessInfoBuilder b, String[] command) {
		b.status = SCHEDULED;
		b.command = command;
	}

	public static void start(ProcessInfoBuilder b, String[] command) {
		if (b.status == CREATED) {
			b.status = LAUNCHING;
			b.command = command;
			b.launch();
		} else {
			if (b.rejected == null) {
				b.rejected = new LinkedList<>();
			}
			long timeStamp = System.currentTimeMillis();
			b.rejected.add(new ProcessInfo(
					b.processData,
					REJECTED,
					command,
					"",
					"rejected duplicated command",
					REJECTED.ordinal(),
					timeStamp,
					timeStamp, null, b.pid));
		}
	}

	public static void failed(ProcessInfoBuilder b, Object dummy) {
		b.status = FAILED;
		b.setReady();
	}

	public static void stop(ProcessInfoBuilder b, Object dummy) {
		if (b.p != null) {
			b.p.destroy();
		}
		if (b.status != LAUNCHING && b.status != RUNNING) {
			b.setReady();
		}
		b.status = STOPPED;
	}

	public static void cancel(ProcessInfoBuilder b, Object dummy) {
		if (b.p != null) {
			b.p.destroy();
		}
		b.setReady();
		b.status = CANCELLED;
	}

	public static void kill(ProcessInfoBuilder b, Object dummy) {
		if (b.p != null) {
			b.p.destroyForcibly();
		}
		if (b.status != LAUNCHING && b.status != RUNNING) {
			b.setReady();
		}
		b.status = KILLED;
	}

	public static void finish(ProcessInfoBuilder b, Integer exitCode) {
		if (b.status != STOPPED && b.status != KILLED && b.status != TIMEOUT) {
			b.status = FINISHED;
		}
		b.exitCode = exitCode;
		b.finished = true;
	}

	public static void stdOut(ProcessInfoBuilder b, Object msg) {
		if (msg == null) {
			b.stdOutClosed = true;
		} else {
			b.stdOut.append(msg).append("\n");
		}
	}

	public static void stdErr(ProcessInfoBuilder b, Object msg) {
		if (msg == null) {
			b.stdErrClosed = true;
		} else {
			b.stdErr.append(msg).append("\n");
		}
	}

	private void launch() {
		DlabProcess.getInstance().getUsersExecutorService(processData.getUser()).submit(() -> {
			status = SCHEDULED;
			DlabProcess.getInstance().getExecutorService().execute(() -> {
				try {
					p = new ProcessBuilder(command).start();
					pid = getPid(p);
					InputStream stdOutStream = p.getInputStream();
					DlabProcess.getInstance().getExecutorService().execute(() -> print(stdOutStream));
					InputStream stdErrStream = p.getErrorStream();
					DlabProcess.getInstance().getExecutorService().execute(() -> printError(stdErrStream));
					status = RUNNING;
					int exit = p.waitFor();
					DlabProcess.getInstance().finish(processData, exit);
				} catch (IOException e) {
					DlabProcess.getInstance().toStdErr(processData, "Command launch failed. " + get().getCommand(), e);
					DlabProcess.getInstance().failed(processData);
				} catch (InterruptedException e) {
					DlabProcess.getInstance().toStdErr(processData, "Command interrupted. " + get().getCommand(), e);
					DlabProcess.getInstance().failed(processData);
					Thread.currentThread().interrupt();
				}
			});
			try {
				future.get();
			} catch (Exception e) {
				log.error("Exception occurred during getting future result: {}", e.getMessage());
			}
		});
	}

	private void printError(InputStream stdErrStream) {
		BufferedReader reader = new BufferedReader(new InputStreamReader(stdErrStream));
		String line;
		try {
			while ((line = reader.readLine()) != null) {
				DlabProcess.getInstance().toStdErr(processData, line);
			}
			DlabProcess.getInstance().toStdErr(processData, null);
		} catch (IOException e) {
			DlabProcess.getInstance().toStdErr(processData, "Failed process STDERR reader", e);
			DlabProcess.getInstance().failed(processData);
		}
	}

	private void print(InputStream stdOutStream) {
		BufferedReader reader = new BufferedReader(new InputStreamReader(stdOutStream));
		String line;
		try {
			while ((line = reader.readLine()) != null) {
				DlabProcess.getInstance().toStdOut(processData, line);
			}
			DlabProcess.getInstance().toStdOut(processData, null);
		} catch (IOException e) {
			DlabProcess.getInstance().toStdErr(processData, "Failed process STDOUT reader", e);
			DlabProcess.getInstance().failed(processData);
		}
	}

	@Override
	public ProcessInfo get() {
		return new ProcessInfo(
				processData,
				status,
				command,
				stdOut.toString(),
				stdErr.toString(),
				exitCode,
				startTimeStamp, System.currentTimeMillis(), rejected, pid);
	}

	@Override
	public boolean test() {
		return finished && stdOutClosed && stdErrClosed;
	}

	private void setReady() {
		finished = true;
		stdOutClosed = true;
		stdErrClosed = true;
	}

	public static void future(ProcessInfoBuilder b, CompletableFuture<ProcessInfo> future) {
		if (b.future == null) {
			b.future = future;
		} else {
			future.cancel(true);
		}
	}

	@Override
	public void onTimeout() {
		if (status != TIMEOUT) {
			log.debug("Stopping on timeout ...");
			stop(this, "STOP");
			status = TIMEOUT;
			expirationTime += 60_000;
		} else {
			log.debug("Killing on timeout ...");
			kill(this, "KILL");
			status = TIMEOUT;
			setReady();
		}
	}

	@Override
	public long getExpirationTime() {
		return expirationTime;
	}

	private static Function<Process, Integer> pidSupplier = null;

	public static int getPid(Process process) {
		try {
			if (pidSupplier == null) {
				Class<?> cProcessImpl = process.getClass();
				final Field fPid = cProcessImpl.getDeclaredField("pid");
				log.debug("PID field found");
				if (!fPid.isAccessible()) {
					fPid.setAccessible(true);
				}
				pidSupplier = p -> {
					try {
						return fPid.getInt(p);
					} catch (IllegalAccessException e) {
						log.error("Unable to access PID. {}", e.getMessage());
						return -1;
					}
				};
			}
			return pidSupplier.apply(process);
		} catch (NoSuchFieldException e) {
			log.debug("PID field not found");
			pidSupplier = p -> -1;
			return -1;
		}
	}

}
