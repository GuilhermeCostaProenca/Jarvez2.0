"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.ArcanistLineageFactoryHandlerDraconic = void 0;
const errors_1 = require("../../../../../../../errors");
const ArcanistLineageDraconic_1 = require("../ArcanistLineageDraconic");
const ArcanistLineageType_1 = require("../ArcanistLineageType");
const ArcanistLineageHandler_1 = require("./ArcanistLineageHandler");
class ArcanistLineageFactoryHandlerDraconic extends ArcanistLineageHandler_1.ArcanistLineageHandler {
    handle(request) {
        if (!request.sorcererLineageDraconicDamageType) {
            throw new errors_1.SheetBuilderError('MISSING_SORCERER_LINEAGE_DRACONIC_DAMAGE_TYPE');
        }
        return new ArcanistLineageDraconic_1.ArcanistLineageDraconic(request.sorcererLineageDraconicDamageType);
    }
    shouldHandle(request) {
        return request.sorcererLineage === ArcanistLineageType_1.ArcanistLineageType.draconic;
    }
}
exports.ArcanistLineageFactoryHandlerDraconic = ArcanistLineageFactoryHandlerDraconic;
