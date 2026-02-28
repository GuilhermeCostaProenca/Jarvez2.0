"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.ArcanistLineageSerializerDraconic = void 0;
const ArcanistLineageSerializer_1 = require("./ArcanistLineageSerializer");
class ArcanistLineageSerializerDraconic extends ArcanistLineageSerializer_1.ArcanistLineageSerializer {
    serialize() {
        return {
            damageType: this.lineage.getDamageType(),
            type: this.lineage.type,
        };
    }
}
exports.ArcanistLineageSerializerDraconic = ArcanistLineageSerializerDraconic;
