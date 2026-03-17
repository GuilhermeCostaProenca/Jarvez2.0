"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.ArcanistLineageSerializerRed = void 0;
const ArcanistLineageSerializer_1 = require("./ArcanistLineageSerializer");
class ArcanistLineageSerializerRed extends ArcanistLineageSerializer_1.ArcanistLineageSerializer {
    serialize() {
        return {
            type: this.lineage.type,
            customTormentaAttribute: this.lineage.getCustomTormentaPowersAttribute(),
            extraPower: this.lineage.getExtraPower().name,
        };
    }
}
exports.ArcanistLineageSerializerRed = ArcanistLineageSerializerRed;
