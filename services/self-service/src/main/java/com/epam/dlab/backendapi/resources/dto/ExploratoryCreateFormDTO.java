/***************************************************************************

 Copyright (c) 2016, EPAM SYSTEMS INC

 Licensed under the Apache License, Version 2.0 (the "License");
 you may not use this file except in compliance with the License.
 You may obtain a copy of the License at

 http://www.apache.org/licenses/LICENSE-2.0

 Unless required by applicable law or agreed to in writing, software
 distributed under the License is distributed on an "AS IS" BASIS,
 WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 See the License for the specific language governing permissions and
 limitations under the License.

 ****************************************************************************/

package com.epam.dlab.backendapi.resources.dto;

import com.fasterxml.jackson.annotation.JsonProperty;
import lombok.Data;
import lombok.ToString;
import org.hibernate.validator.constraints.NotBlank;

/**
 * Stores info about new exploratory.
 */
@Data
@ToString
public class ExploratoryCreateFormDTO {
	@NotBlank
	@JsonProperty
	private String image;

	@NotBlank
	@JsonProperty("template_name")
	private String templateName;

	@NotBlank
	@JsonProperty
	private String name;

	@NotBlank
	@JsonProperty
	private String shape;

	@NotBlank
	@JsonProperty("disk_size")
	private String diskSize;

	@NotBlank
	@JsonProperty
	private String version;

	@JsonProperty("notebook_image_name")
	private String imageName;
}
