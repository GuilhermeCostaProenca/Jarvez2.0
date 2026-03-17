"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.ArcanistLineageSerializedHandlerDraconic = void 0;
const errors_1 = require("../../../../../../../errors");
const ArcanistLineageDraconic_1 = require("../ArcanistLineageDraconic");
const ArcanistLineageType_1 = require("../ArcanistLineageType");
const ArcanistLineageSerializedHandler_1 = require("./ArcanistLineageSerializedHandler");
class ArcanistLineageSerializedHandlerDraconic extends ArcanistLineageSerializedHandler_1.ArcanistLineageSerializedHandler {
    handle(request) {
        if (!request.damageType) {
            throw new errors_1.SheetBuilderError('MISSING_SORCERER_LINEAGE_DRACONIC_DAMAGE_TYPE');
        }
        return new ArcanistLineageDraconic_1.ArcanistLineageDraconic(request.damageType);
    }
    shouldHandle(request) {
        return request.type === ArcanistLineageType_1.ArcanistLineageType.draconic;
    }
}
exports.ArcanistLineageSerializedHandlerDraconic = ArcanistLineageSerializedHandlerDraconic;
