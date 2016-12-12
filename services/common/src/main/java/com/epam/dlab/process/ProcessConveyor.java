package com.epam.dlab.process;/*
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

import com.aegisql.conveyor.AssemblingConveyor;
import com.aegisql.conveyor.BuildingSite;
import com.aegisql.conveyor.cart.Cart;
import com.aegisql.conveyor.cart.FutureCart;

import java.util.HashMap;
import java.util.Map;
import java.util.concurrent.ConcurrentHashMap;
import java.util.concurrent.ConcurrentLinkedQueue;
import java.util.concurrent.TimeUnit;
import java.util.concurrent.atomic.AtomicInteger;
import java.util.function.Supplier;

public class ProcessConveyor extends AssemblingConveyor<ProcessId,ProcessStep,ProcessInfo>{

    private final ConcurrentHashMap<String,ConcurrentLinkedQueue<String>> users = new ConcurrentHashMap<>();

    private int maxUserCommands = 5;

    public ProcessConveyor() {
        super();
        this.setName("ProcessConveyor");
        this.setIdleHeartBeat(1, TimeUnit.SECONDS);
        this.setDefaultBuilderTimeout(3,TimeUnit.HOURS);
        this.setDefaultCartConsumer((l,v,b)->{
            LOG.warn("default processor for {} {} {}",l,v,b.get());
            if(v instanceof FutureCart) {
                FutureCart fc = (FutureCart)v;
                fc.get().cancel(true);
            }
        });
        this.setResultConsumer((bin)->{
            LOG.debug("process finished: {}",bin);
        });

    }

    public Supplier<? extends ProcessInfo> getInfoSupplier(ProcessId id) {
        BuildingSite<ProcessId, ProcessStep, Cart<ProcessId, ?, ProcessStep>, ? extends ProcessInfo> bs = this.collector.get(id);
        if(bs == null) {
            return () -> null;
        } else {
            return bs.getProductSupplier();
        }
    }

    public void setMaxUserProcesses(int maxUserCommands) {
        this.maxUserCommands = maxUserCommands;
    }

}
