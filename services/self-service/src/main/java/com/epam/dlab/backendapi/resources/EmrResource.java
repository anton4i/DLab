package com.epam.dlab.backendapi.resources;

import com.epam.dlab.auth.UserInfo;
import com.epam.dlab.backendapi.api.EMRCreateFormDTO;
import com.epam.dlab.backendapi.client.rest.EmrAPI;
import com.epam.dlab.backendapi.dao.KeyDAO;
import com.epam.dlab.backendapi.dao.SettingsDAO;
import com.epam.dlab.client.restclient.RESTService;
import com.epam.dlab.dto.ResourceDTO;
import com.epam.dlab.dto.EMRCreateDTO;
import com.google.inject.Inject;
import com.google.inject.name.Named;
import io.dropwizard.auth.Auth;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

import javax.ws.rs.Consumes;
import javax.ws.rs.POST;
import javax.ws.rs.Path;
import javax.ws.rs.Produces;
import javax.ws.rs.core.MediaType;

import java.io.IOException;

import static com.epam.dlab.backendapi.SelfServiceApplicationConfiguration.PROVISIONING_SERVICE;

/**
 * Created by Maksym_Pendyshchuk on 10/17/2016.
 */
@Path("/emr")
@Consumes(MediaType.APPLICATION_JSON)
@Produces(MediaType.APPLICATION_JSON)
public class EmrResource implements EmrAPI {
    private static final Logger LOGGER = LoggerFactory.getLogger(EmrResource.class);

    @Inject
    private SettingsDAO dao;
    @Inject
    private KeyDAO keyDao;
    @Inject
    @Named(PROVISIONING_SERVICE)
    private RESTService provisioningService;

    @POST
    @Path("/create")
    public String create(@Auth UserInfo userInfo, EMRCreateFormDTO formDTO) throws IOException {
        LOGGER.debug("creating emr {}", userInfo.getName());
        EMRCreateDTO dto = new EMRCreateDTO();
        dto.setServiceBaseName(dao.getServiceBaseName());
        dto.setInstanceCount(formDTO.getInstanceCount());
        dto.setInstanceType(formDTO.getInstanceType());
        dto.setVersion(formDTO.getVersion());
        dto.setNotebookName(formDTO.getNotebookName());
        dto.setNotebookName(userInfo.getName());
        dto.setEdgeSubnet(keyDao.findCredential(userInfo.getName()).getNotebookSubnet());
        dto.setRegion(dao.getAwsRegion());
        return provisioningService.post(EMR_CREATE, dto, String.class);
    }

    @POST
    @Path("/terminate")
    public String terminate(@Auth UserInfo userInfo, String emr) {
        LOGGER.debug("terminating emr {}", userInfo.getName());
        ResourceDTO emrCluster = new ResourceDTO()
                .withName(emr)
                .withUser(userInfo.getName())
                .withRegion(dao.getAwsRegion());
        return provisioningService.post(EMR_TERMINATE, emrCluster, String.class);
    }
}
