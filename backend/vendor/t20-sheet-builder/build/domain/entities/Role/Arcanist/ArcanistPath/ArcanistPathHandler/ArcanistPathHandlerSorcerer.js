"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.ArcanistPathHandlerSorcerer = void 0;
const errors_1 = require("../../../../../errors");
const ArcanistPath_1 = require("../ArcanistPath");
const ArcanistPathSorcerer_1 = require("../ArcanistPathSorcerer");
const ArcanistPathHandler_1 = require("./ArcanistPathHandler");
class ArcanistPathHandlerSorcerer extends ArcanistPathHandler_1.ArcanistPathHandler {
    handle(request) {
        if (!request.sorcererLineage) {
            throw new errors_1.SheetBuilderError('MISSING_SORCERER_LINEAGE');
        }
        const draconic = new ArcanistPathSorcerer_1.ArcanistLineageFactoryHandlerDraconic();
        const faerie = new ArcanistPathSorcerer_1.ArcanistLineageFactoryHandlerFaerie();
        const red = new ArcanistPathSorcerer_1.ArcanistLineageFactoryHandlerRed();
        draconic
            .setNext(faerie)
            .setNext(red);
        const lineage = draconic.execute({
            mageSpell: request.mageSpell,
            wizardFocus: request.wizardFocus,
            sorcererLineageDraconicDamageType: request.sorcererLineageDraconicDamageType,
            sorcererLineageFaerieExtraSpell: request.sorcererLineageFaerieExtraSpell,
            sorcererLineage: request.sorcererLineage,
            sorcererLineageRedAttribute: request.sorcererLineageRedAttribute,
            sorcererLineageRedExtraPower: request.sorcererLineageRedExtraPower,
        });
        return new ArcanistPathSorcerer_1.ArcanistPathSorcerer(lineage);
    }
    shouldHandle(request) {
        return request.path === ArcanistPath_1.ArcanistPathName.sorcerer;
    }
}
exports.ArcanistPathHandlerSorcerer = ArcanistPathHandlerSorcerer;
