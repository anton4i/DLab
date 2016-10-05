package com.epam.dlab.auth;

import com.fasterxml.jackson.annotation.JsonCreator;
import com.fasterxml.jackson.annotation.JsonProperty;
import com.fasterxml.jackson.annotation.JsonSetter;

import java.security.Principal;
import java.util.Arrays;
import java.util.Collection;
import java.util.HashSet;
import java.util.Set;

public class UserInfo implements Principal {

    private final String username;
    private final String accessToken;
    private final Set<String> roles = new HashSet<>();

    @JsonProperty
    private String firstName;
    @JsonProperty
    private String lastName;

    @JsonCreator
    public UserInfo(@JsonProperty("username") String username, @JsonProperty("access_token") String accessToken) {
        this.username = username;
        this.accessToken = accessToken;
    }

    @Override
    @JsonProperty("username")
    public String getName() {
        return username;
    }

    @JsonProperty("access_token")
    public String getAccessToken() {
        return accessToken;
    }

    @JsonProperty("roles")
    public Collection<String> getRoles() {
        return roles;
    }

    //@JsonSetter("roles")
    public void addRoles(Collection<String> roles) {
        roles.addAll(roles);
    }

    @JsonSetter("roles")
    public void addRoles(String[] r) {
        roles.addAll(Arrays.asList(r));
    }

    public void addRole(String role) {
        roles.add(role);
    }


    public String getFirstName() {
        return firstName;
    }

    public void setFirstName(String firstName) {
        this.firstName = firstName;
    }

    public String getLastName() {
        return lastName;
    }

    public void setLastName(String lastName) {
        this.lastName = lastName;
    }

    public UserInfo withToken(String token) {
        UserInfo newInfo = new UserInfo(username, token);
        roles.forEach(role -> newInfo.addRole(role));
        newInfo.firstName = this.firstName;
        newInfo.lastName = this.lastName;
        return newInfo;
    }

    @Override
    public int hashCode() {
        final int prime = 31;
        int result = 1;
        result = prime * result + ((accessToken == null) ? 0 : accessToken.hashCode());
        result = prime * result + ((firstName == null) ? 0 : firstName.hashCode());
        result = prime * result + ((lastName == null) ? 0 : lastName.hashCode());
        result = prime * result + ((roles == null) ? 0 : roles.hashCode());
        result = prime * result + ((username == null) ? 0 : username.hashCode());
        return result;
    }

    @Override
    public boolean equals(Object obj) {
        if (this == obj)
            return true;
        if (obj == null)
            return false;
        if (getClass() != obj.getClass())
            return false;
        UserInfo other = (UserInfo) obj;
        if (accessToken == null) {
            if (other.accessToken != null)
                return false;
        } else if (!accessToken.equals(other.accessToken))
            return false;
        if (firstName == null) {
            if (other.firstName != null)
                return false;
        } else if (!firstName.equals(other.firstName))
            return false;
        if (lastName == null) {
            if (other.lastName != null)
                return false;
        } else if (!lastName.equals(other.lastName))
            return false;
        if (roles == null) {
            if (other.roles != null)
                return false;
        } else if (!roles.equals(other.roles))
            return false;
        if (username == null) {
            if (other.username != null)
                return false;
        } else if (!username.equals(other.username))
            return false;
        return true;
    }

    @Override
    public String toString() {
        return "UserInfo [username=" + username + ", firstName=" + firstName + ", lastName=" + lastName + ", roles="
                + roles + ", accessToken=" + accessToken + "]";
    }


}
