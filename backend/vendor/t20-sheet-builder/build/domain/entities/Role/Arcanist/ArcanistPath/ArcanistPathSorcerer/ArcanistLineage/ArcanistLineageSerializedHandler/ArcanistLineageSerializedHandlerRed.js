"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.ArcanistLineageSerializedHandlerRed = void 0;
const errors_1 = require("../../../../../../../errors");
const Power_1 = require("../../../../../../Power");
const ArcanistLineageRed_1 = require("../ArcanistLineageRed");
const ArcanistLineageType_1 = require("../ArcanistLineageType");
const ArcanistLineageSerializedHandler_1 = require("./ArcanistLineageSerializedHandler");
class ArcanistLineageSerializedHandlerRed extends ArcanistLineageSerializedHandler_1.ArcanistLineageSerializedHandler {
    handle(request) {
        if (!request.customTormentaAttribute) {
            throw new errors_1.SheetBuilderError('MISSING_SORCERER_LINEAGE_RED_ATTRIBUTE');
        }
        if (!request.extraPower) {
            throw new errors_1.SheetBuilderError('MISSING_SORCERER_LINEAGE_RED_EXTRA_POWER');
        }
        const power = Power_1.GeneralPowerFactory.make({ name: request.extraPower });
        return new ArcanistLineageRed_1.ArcanistLineageRed(power, request.customTormentaAttribute);
    }
    shouldHandle(request) {
        return request.type === ArcanistLineageType_1.ArcanistLineageType.red;
    }
}
exports.ArcanistLineageSerializedHandlerRed = ArcanistLineageSerializedHandlerRed;
