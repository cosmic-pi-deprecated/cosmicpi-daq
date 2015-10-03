package org.cosmicpi.daq;

import com.google.gson.Gson;
import com.google.gson.JsonSyntaxException;
import lombok.extern.slf4j.Slf4j;
import org.elasticsearch.common.collect.Lists;
import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;
import org.springframework.context.ConfigurableApplicationContext;
import org.springframework.data.elasticsearch.core.ElasticsearchTemplate;
import org.springframework.data.elasticsearch.core.geo.GeoPoint;
import org.springframework.data.elasticsearch.core.query.IndexQuery;
import org.springframework.data.elasticsearch.core.query.IndexQueryBuilder;

import java.sql.Timestamp;
import java.util.Arrays;
import java.util.List;
import java.util.Random;
import java.util.stream.Collectors;
import java.util.stream.Stream;

import static org.cosmicpi.daq.CosmicEvent.*;

/**
 * Created by jsalmon on 19/06/15.
 */
@Slf4j
@SpringBootApplication
public class Application {

  public static void main(String[] args) throws InterruptedException {
    ConfigurableApplicationContext context = SpringApplication.run(Application.class, args);

    SerialPortManager manager = context.getBean(SerialPortManager.class);
    ElasticsearchTemplate elasticsearchTemplate = context.getBean(ElasticsearchTemplate.class);

//    elasticsearchTemplate.deleteIndex(CosmicEvent.class);
    if (!elasticsearchTemplate.indexExists(CosmicEvent.class)) {
      elasticsearchTemplate.createIndex(CosmicEvent.class);
      elasticsearchTemplate.refresh(CosmicEvent.class, true);
      elasticsearchTemplate.putMapping(CosmicEvent.class);
    }

//    while (true) {
//
////      Integer id = 1;
//      String gps = "$GPGGA,224116.473,2.604,N,00726.691,E,0,00,5,2.2,M,0,M,0,*5E";
//      NMEAParser.GPSPosition position = new NMEAParser().parse(gps);
//
//      GeoPoint geoPoint = new GeoPoint(46.2362, 6.048703);
//
//      List<Integer> channel1 = new Random().ints(1, 100).limit(10).boxed().collect(Collectors.toList());
//      List<Integer> channel2 = new Random().ints(1, 100).limit(10).boxed().collect(Collectors.toList());
//      Energy energy = new Energy(channel1, channel2);
//
//      Double timing = 1.0;
//      Double altitude = 1.0;
//      Double humidity = 1.0;
//
//      GravitationalOrientation gravitationalOrientation = new GravitationalOrientation(1.0, 2.0, 3.0);
//      MagneticOrientation magneticOrientation = new MagneticOrientation(1.0, 2.0, 3.0);
//      Temperature temperature = new Temperature(10.0, 11.0);
//
//      Double uptime = 1.0;
//
//      CosmicEvent event = new CosmicEvent(gps, geoPoint, new Timestamp(System.currentTimeMillis()), timing, energy, altitude, humidity,
//          gravitationalOrientation, magneticOrientation, temperature, uptime);
//
//      IndexQuery query = new IndexQueryBuilder().withIndexName("events").withObject(event).build();
//      elasticsearchTemplate.index(query);
//      log.info(event.toString());
//
//      Thread.sleep(1000);
//    }

    final int[] i = {0};

    manager.addEventListener(line -> {

      CosmicEvent event = null;

      try {
        event = new Gson().fromJson(line, CosmicEvent.class);
      } catch (JsonSyntaxException e) {
        log.trace("error parsing event: " + e.toString());
      }

      if (event != null) {
        i[0]++;
        event.setTimestamp(new Timestamp(System.currentTimeMillis()));

        NMEAParser.GPSPosition position = new NMEAParser().parse(event.getGps());
        event.setGeoPoint(new GeoPoint(position.lat, position.lon));

        EnergyChannel channel1 = new EnergyChannel(event.getEnergy().getEnergy1());
        EnergyChannel channel2 = new EnergyChannel(event.getEnergy().getEnergy2());

        event.setChannel1(channel1);
        event.setChannel2(channel2);

        IndexQuery query = new IndexQueryBuilder().withIndexName("events").withObject(event).build();
        elasticsearchTemplate.index(query);

        log.info("event " + i[0] + ": " + event.toString());
      }
    });
  }
}
