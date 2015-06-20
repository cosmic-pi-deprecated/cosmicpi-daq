package org.cosmicpi.daq;

import cern.c2mon.shared.common.datatag.address.impl.HardwareAddressImpl;
import org.simpleframework.xml.Element;

/**
 * Created by jsalmon on 20/06/15.
 */
public class CosmicPiHardwareAddress extends HardwareAddressImpl {

    private static final long serialVersionUID = 3098291787686272949L;

    @Element
    protected String id;

    public CosmicPiHardwareAddress() {

    }

    public CosmicPiHardwareAddress(String id) {
        this.id = id;
    }

    public String getId() {
        return id;
    }

    public void setId(String id) {
        this.id = id;
    }
}
