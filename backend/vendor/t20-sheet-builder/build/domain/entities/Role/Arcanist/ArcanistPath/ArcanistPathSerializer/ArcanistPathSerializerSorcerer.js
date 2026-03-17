"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.ArcanistPathSerializerSorcerer = void 0;
const errors_1 = require("../../../../../errors");
const ArcanistPathSorcerer_1 = require("../ArcanistPathSorcerer");
const ArcanistPathSerializer_1 = require("./ArcanistPathSerializer");
class ArcanistPathSerializerSorcerer extends ArcanistPathSerializer_1.ArcanistPathSerializer {
    constructor(path) {
        super();
        this.path = path;
        this.lineageSerializer = this.getLineageSerializer(path.lineage);
    }
    serialize() {
        return {
            lineage: this.lineageSerializer.serialize(),
            name: this.path.pathName,
        };
    }
    getLineageSerializer(lineage) {
        if (lineage instanceof ArcanistPathSorcerer_1.ArcanistLineageDraconic) {
            return new ArcanistPathSorcerer_1.ArcanistLineageSerializerDraconic(lineage);
        }
        if (lineage instanceof ArcanistPathSorcerer_1.ArcanistLineageFaerie) {
            return new ArcanistPathSorcerer_1.ArcanistLineageSerializerFaerie(lineage);
        }
        if (lineage instanceof ArcanistPathSorcerer_1.ArcanistLineageRed) {
            return new ArcanistPathSorcerer_1.ArcanistLineageSerializerRed(lineage);
        }
        throw new errors_1.SheetBuilderError('INVALID_LINEAGE');
    }
}
exports.ArcanistPathSerializerSorcerer = ArcanistPathSerializerSorcerer;
