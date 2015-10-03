package org.cosmicpi.daq;

import lombok.Data;

import java.util.List;

/**
 * Created by justin on 03/10/2015.
 */
@Data
public class EnergyChannel {
  private Integer value0;
  private Integer value1;
  private Integer value2;
  private Integer value3;
  private Integer value4;
  private Integer value5;
  private Integer value6;
  private Integer value7;
  private Integer value8;
  private Integer value9;

  public EnergyChannel(List<Integer> channel) {
    value0 = channel.get(0);
    value1 = channel.get(1);
    value2 = channel.get(2);
    value3 = channel.get(3);
    value4 = channel.get(4);
    value5 = channel.get(5);
    value6 = channel.get(6);
    value7 = channel.get(7);
    value8 = channel.get(8);
    value9 = channel.get(9);
  }
}
