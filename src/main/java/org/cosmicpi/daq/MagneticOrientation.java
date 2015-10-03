package org.cosmicpi.daq;

import lombok.AllArgsConstructor;
import lombok.Data;

/**
 * Created by justin on 02/10/2015.
 */
@Data
@AllArgsConstructor
public class MagneticOrientation {
  private Double x;
  private Double y;
  private Double z;
}
