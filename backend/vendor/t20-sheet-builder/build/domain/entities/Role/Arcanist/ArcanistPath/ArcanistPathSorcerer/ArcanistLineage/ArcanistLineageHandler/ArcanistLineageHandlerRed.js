"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.ArcanistLineageFactoryHandlerRed = void 0;
const errors_1 = require("../../../../../../../errors");
const Power_1 = require("../../../../../../Power");
const ArcanistLineageRed_1 = require("../ArcanistLineageRed");
const ArcanistLineageType_1 = require("../ArcanistLineageType");
const ArcanistLineageHandler_1 = require("./ArcanistLineageHandler");
class ArcanistLineageFactoryHandlerRed extends ArcanistLineageHandler_1.ArcanistLineageHandler {
    handle(request) {
        if (!request.sorcererLineageRedAttribute) {
            throw new errors_1.SheetBuilderError('MISSING_SORCERER_LINEAGE_RED_ATTRIBUTE');
        }
        if (!request.sorcererLineageRedExtraPower) {
            throw new errors_1.SheetBuilderError('MISSING_SORCERER_LINEAGE_RED_EXTRA_POWER');
        }
        const power = Power_1.GeneralPowerFactory.make({ name: request.sorcererLineageRedExtraPower });
        return new ArcanistLineageRed_1.ArcanistLineageRed(power, request.sorcererLineageRedAttribute);
    }
    shouldHandle(request) {
        return request.sorcererLineage === ArcanistLineageType_1.ArcanistLineageType.red;
    }
}
exports.ArcanistLineageFactoryHandlerRed = ArcanistLineageFactoryHandlerRed;
