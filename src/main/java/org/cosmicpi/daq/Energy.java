package org.cosmicpi.daq;

import lombok.AllArgsConstructor;
import lombok.Data;

import java.util.List;

/**
 * Created by justin on 02/10/2015.
 */
@Data
@AllArgsConstructor
public class Energy {
  private List<Integer> energy1;
  private List<Integer> energy2;
}
