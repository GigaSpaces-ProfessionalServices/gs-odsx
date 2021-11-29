package com.gigaspaces.odsx.noderebalancer.util;

import com.gigaspaces.odsx.noderebalancer.model.Pair;
import org.openspaces.admin.machine.Machine;
import org.openspaces.admin.vm.VirtualMachine;
import org.openspaces.admin.vm.VirtualMachineStatistics;

import java.util.List;

public class MachineFinder {
    public Pair<Machine, Long> findMachineWithRAM(Machine[] machines) {
       return  findMachineWithRAM(machines, null);
    }
     public Pair<Machine, Long> findMachineWithRAM(Machine[] machines, List<String> matchingServers){
        Machine machineWithMostAvailableMemory = null;
        long largestMemoryAvailable = 0;
        if (machines != null && machines.length > 0){
            for (Machine machine : machines){

                long totalMemorySize = getTotalMemory(machine);

                long totalVMMemory = getTotalVMMemory(machine);

                long availableMemory = totalMemorySize - totalVMMemory;

                if(availableMemory > largestMemoryAvailable && machineMatches(machine.getHostAddress(), matchingServers)){
                    largestMemoryAvailable = availableMemory;
                    machineWithMostAvailableMemory = machine;
                }
            }
        }
        //TODO: Check if the available RAM is less than needed than log the fact and dont attempt to create the container
        return new Pair<Machine, Long>( machineWithMostAvailableMemory, largestMemoryAvailable);
    }

    private boolean machineMatches(String hostAddress, List<String> matchingServers) {
        if(matchingServers == null){
            return true;
        }
        return (matchingServers.contains(hostAddress));
    }

    public long getTotalVMMemory(Machine machine) {
        VirtualMachine virtualMachines[] = machine.getVirtualMachines().getVirtualMachines();
        long totalVMMemory = 0;
        for( VirtualMachine virtualMachine : virtualMachines){
            VirtualMachineStatistics vmStatistics = virtualMachine.getStatistics();
            long vmMemory = vmStatistics.getMemoryHeapCommittedInBytes() + vmStatistics.getMemoryNonHeapCommittedInBytes();
            totalVMMemory += vmMemory;
        }
        return totalVMMemory;
    }

    public long getTotalMemory(Machine machine) {
        long totalMemorySize = machine.getOperatingSystem().getDetails().getTotalPhysicalMemorySizeInBytes();
        return totalMemorySize;
    }

}
