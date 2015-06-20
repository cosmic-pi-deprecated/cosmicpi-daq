package org.cosmicpi.daq;


import cern.c2mon.daq.common.EquipmentMessageHandler;
import cern.c2mon.daq.tools.equipmentexceptions.EqIOException;
import cern.c2mon.shared.common.datatag.ISourceDataTag;
import com.google.gson.Gson;
import com.google.gson.JsonSyntaxException;

/**
 * Created by jsalmon on 20/06/15.
 */
public class CosmicMessageHandler extends EquipmentMessageHandler {
    @Override
    public void connectToDataSource() throws EqIOException {

        SerialPortManager manager = new SerialPortManager();

        manager.addEventListener(new SerialPortManager.CosmicEventListener() {
            @Override
            public void onEvent(String line) {

                for (ISourceDataTag dataTag : getEquipmentConfiguration().getSourceDataTags().values()) {

                    Gson gson = new Gson();
                    CosmicEvent event = null;
                    try {
                        event = gson.fromJson(line, CosmicEvent.class);
                    } catch (JsonSyntaxException e) {
                        System.out.println("error parsing json: " + e.toString());
                    }

                    if (event != null) {

                        if (dataTag.getName().contains("PACKET")) {
                            System.out.println("Sending event packet: " + event.toString());
                            getEquipmentMessageSender().sendTagFiltered(dataTag, gson.toJson(event), System.currentTimeMillis());

                        } else if (dataTag.getName().contains("CHANNEL1")) {
                            System.out.println("Sending channel 1 energy: " + event.getEnergy().getChannel1());
                            getEquipmentMessageSender().sendTagFiltered(dataTag, event.getEnergy().getChannel1(), System.currentTimeMillis());

                        } else if (dataTag.getName().contains("CHANNEL2")) {
                            System.out.println("Sending channel 2 energy: " + event.getEnergy().getChannel2());
                            getEquipmentMessageSender().sendTagFiltered(dataTag, event.getEnergy().getChannel2(), System.currentTimeMillis());
                        }

                    }
                }
            }
        });


    }

    @Override
    public void disconnectFromDataSource() throws EqIOException {

    }

    @Override
    public void refreshAllDataTags() {

    }

    @Override
    public void refreshDataTag(long l) {

    }
}
