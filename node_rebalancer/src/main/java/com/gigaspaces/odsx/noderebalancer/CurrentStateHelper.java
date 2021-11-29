package com.gigaspaces.odsx.noderebalancer;

import com.gigaspaces.odsx.noderebalancer.admin.model.ContainerConfiguration;
import org.openspaces.admin.machine.Machine;

import java.util.ArrayList;

public interface CurrentStateHelper {

    Machine geMachineWithMostFreeMemory();

    void addContainerForReBalancing(String targetHostName, String targetHostAddress, ArrayList<ContainerConfiguration> container);

    Machine getMachine(String hostIP);
}
