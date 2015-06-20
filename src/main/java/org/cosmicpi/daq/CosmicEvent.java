package org.cosmicpi.daq;

/**
 * Created by jsalmon on 20/06/15.
 */
public class CosmicEvent {

    private Integer id;

    private GPS gps;

    private Double timing;

    private Energy energy;

    private Double altitude;

    private Double humidity;

    private GravitationalOrientation gravitationalOrientation;

    private MagneticOrientation magneticOrientation;

    private Temperature temperature;

    private Double uptime;

    public Energy getEnergy() {
        return energy;
    }

    @Override
    public String toString() {
        return String.format(
                "CosmicEvent[id=%d, channel1='%f', channel2='%f']",
                id, energy.channel1, energy.channel2);
    }

    class GPS {
        private Double time;

        private Double latitude;

        private Double longitude;

        private Double quality;

        private Integer numSatellites;

        private Double horizontalAccuracy;

        private Double altitude;

        private Double height;

        private Double dgps;

        private String checksum;
    }

    class Energy {
        private Double channel1;

        private Double channel2;

        public Double getChannel1() {
            return channel1;
        }

        public Double getChannel2() {
            return channel2;
        }
    }

    class GravitationalOrientation {
        private Double x;
        private Double y;
        private Double z;
    }

    class MagneticOrientation {
        private Double x;
        private Double y;
        private Double z;
    }

    class Temperature {
        private Double value1;
        private Double value2;
    }
}
