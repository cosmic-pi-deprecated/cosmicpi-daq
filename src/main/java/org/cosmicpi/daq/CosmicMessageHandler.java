//package org.cosmicpi.daq;
//
//
//import cern.c2mon.daq.common.EquipmentMessageHandler;
//import cern.c2mon.daq.common.IEquipmentMessageSender;
//import cern.c2mon.daq.common.impl.EquipmentMessageSender;
//import cern.c2mon.daq.tools.equipmentexceptions.EqIOException;
//import cern.c2mon.shared.common.datatag.ISourceDataTag;
//import cern.c2mon.shared.common.process.EquipmentConfiguration;
//import cern.c2mon.shared.common.process.IEquipmentConfiguration;
//import com.google.gson.Gson;
//import com.google.gson.JsonSyntaxException;
//
///**
// * Created by jsalmon on 20/06/15.
// */
//public class CosmicMessageHandler extends EquipmentMessageHandler {
//    @Override
//    public void connectToDataSource() throws EqIOException {
//
//        IEquipmentConfiguration configuration = getEquipmentConfiguration();
//        SerialPortManager manager = new SerialPortManager();
//
//        manager.addEventListener(new SerialPortManager.CosmicEventListener() {
//            @Override
//            public void onEvent(String line) {
//
//                for (ISourceDataTag dataTag : configuration.getSourceDataTags().values()) {
//
//                    Gson gson = new Gson();
//                    CosmicEvent event = null;
//                    try {
//                        event = gson.fromJson(line, CosmicEvent.class);
//                    } catch (JsonSyntaxException e) {
//                        System.out.println("error parsing json: " + e.toString());
//                    }
//
//                    if (event != null) {
//
//                        if (dataTag.getName().contains("PACKET")) {
//                            System.out.println("Sending event packet: " + event.toString());
//                            getEquipmentMessageSender().sendTagFiltered(dataTag, gson.toJson(event), System.currentTimeMillis());
//
//                        } else if (dataTag.getName().contains("CHANNEL1")) {
//                            System.out.println("Sending channel 1 energy: " + event.getEnergy().getChannel1());
//                            getEquipmentMessageSender().sendTagFiltered(dataTag, event.getEnergy().getChannel1(), System.currentTimeMillis());
//
//                        } else if (dataTag.getName().contains("CHANNEL2")) {
//                            System.out.println("Sending channel 2 energy: " + event.getEnergy().getChannel2());
//                            getEquipmentMessageSender().sendTagFiltered(dataTag, event.getEnergy().getChannel2(), System.currentTimeMillis());
//                        }
//
//                    }
//                }
//            }
//        });
//
//
//        new Thread(new Runnable() {
//            @Override
//            public void run() {
//                IEquipmentMessageSender sender = getEquipmentMessageSender();
//
//                while (true) {
//                    System.out.println("Sending DAQ heartbeat");
//                    sender.sendSupervisionAlive();
//
//                    try {
//                        Thread.sleep(30000);
//                    } catch (InterruptedException e) {
//                        e.printStackTrace();
//                    }
//                }
//            }
//        }).start();
//    }
//
//    @Override
//    public void disconnectFromDataSource() throws EqIOException {
//
//    }
//
//    @Override
//    public void refreshAllDataTags() {
//
//    }
//
//    @Override
//    public void refreshDataTag(long l) {
//
//    }
//}
