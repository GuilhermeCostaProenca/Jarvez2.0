"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.ArcanistLineageFactoryHandlerFaerie = void 0;
const errors_1 = require("../../../../../../../errors");
const Spell_1 = require("../../../../../../Spell");
const ArcanistLineageFaerie_1 = require("../ArcanistLineageFaerie");
const ArcanistLineageType_1 = require("../ArcanistLineageType");
const ArcanistLineageHandler_1 = require("./ArcanistLineageHandler");
class ArcanistLineageFactoryHandlerFaerie extends ArcanistLineageHandler_1.ArcanistLineageHandler {
    handle(request) {
        if (!request.sorcererLineageFaerieExtraSpell) {
            throw new errors_1.SheetBuilderError('MISSING_SORCERER_LINEAGE_FAERIE_DAMAGE_TYPE');
        }
        const spell = Spell_1.SpellFactory.make(request.sorcererLineageFaerieExtraSpell);
        return new ArcanistLineageFaerie_1.ArcanistLineageFaerie(spell);
    }
    shouldHandle(request) {
        return request.sorcererLineage === ArcanistLineageType_1.ArcanistLineageType.faerie;
    }
}
exports.ArcanistLineageFactoryHandlerFaerie = ArcanistLineageFactoryHandlerFaerie;
