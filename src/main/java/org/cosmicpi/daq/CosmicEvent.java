package org.cosmicpi.daq;

import com.fasterxml.jackson.annotation.JsonFormat;
import com.fasterxml.jackson.annotation.JsonProperty;
import lombok.AllArgsConstructor;
import lombok.Data;
import org.springframework.data.elasticsearch.annotations.Document;
import org.springframework.data.elasticsearch.core.geo.GeoPoint;

import java.sql.Timestamp;
import java.util.List;

/**
 * Created by jsalmon on 20/06/15.
 */
@Data
@AllArgsConstructor
@Document(indexName = "events")
public class CosmicEvent {

  private String gps;
  private GeoPoint geoPoint;

  @JsonProperty(value = "@timestamp")
  @JsonFormat(shape = JsonFormat.Shape.STRING, pattern ="yyyy-MM-dd'T'HH:mm:ss.SSSZZ")
  private Timestamp timestamp;

  private Double timing;

  private Energy energy;
  private EnergyChannel channel1;
  private EnergyChannel channel2;

  private Double altitude;
  private Double humidity;
  private GravitationalOrientation gravitationalOrientation;
  private MagneticOrientation magneticOrientation;
  private Temperature temperature;
  private Double uptime;
}
