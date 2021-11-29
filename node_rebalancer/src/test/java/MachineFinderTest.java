import com.gigaspaces.odsx.noderebalancer.util.MachineFinder;
import com.gigaspaces.odsx.noderebalancer.model.Pair;
import org.junit.jupiter.api.Test;
import org.openspaces.admin.machine.Machine;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.mockito.Mockito.mock;
import static org.mockito.Mockito.when;

public class MachineFinderTest {

    @Test
    public void testMachienWithMostMemoryFound(){
        Machine mockedMachine = mock(Machine.class);
        Machine []machines = {mockedMachine, mockedMachine,mockedMachine};

        MachineFinder machineFinderPartialMock = mock(MachineFinder.class);
        when(machineFinderPartialMock.getTotalVMMemory(mockedMachine)).thenReturn(500L).thenReturn(1200L).thenReturn(900L);
        when(machineFinderPartialMock.getTotalMemory(mockedMachine)).thenReturn(1000L).thenReturn(2000L).thenReturn(1500L);
        when(machineFinderPartialMock.findMachineWithRAM(machines)).thenCallRealMethod();

        Pair<Machine, Long> result = machineFinderPartialMock.findMachineWithRAM(machines);

        assertEquals(800L, result.getSecond());

    }
}
