"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.ArcanistLineageSerializerFaerie = void 0;
const ArcanistLineageSerializer_1 = require("./ArcanistLineageSerializer");
class ArcanistLineageSerializerFaerie extends ArcanistLineageSerializer_1.ArcanistLineageSerializer {
    serialize() {
        return {
            type: this.lineage.type,
            extraSpell: this.lineage.getExtraSpell().name,
        };
    }
}
exports.ArcanistLineageSerializerFaerie = ArcanistLineageSerializerFaerie;
