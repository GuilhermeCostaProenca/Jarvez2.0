"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.ArcanistLineageSerializedHandlerFaerie = void 0;
const errors_1 = require("../../../../../../../errors");
const Spell_1 = require("../../../../../../Spell");
const ArcanistLineageFaerie_1 = require("../ArcanistLineageFaerie");
const ArcanistLineageType_1 = require("../ArcanistLineageType");
const ArcanistLineageSerializedHandler_1 = require("./ArcanistLineageSerializedHandler");
class ArcanistLineageSerializedHandlerFaerie extends ArcanistLineageSerializedHandler_1.ArcanistLineageSerializedHandler {
    handle(request) {
        if (!request.extraSpell) {
            throw new errors_1.SheetBuilderError('MISSING_SORCERER_LINEAGE_FAERIE_DAMAGE_TYPE');
        }
        const spell = Spell_1.SpellFactory.make(request.extraSpell);
        return new ArcanistLineageFaerie_1.ArcanistLineageFaerie(spell);
    }
    shouldHandle(request) {
        return request.type === ArcanistLineageType_1.ArcanistLineageType.faerie;
    }
}
exports.ArcanistLineageSerializedHandlerFaerie = ArcanistLineageSerializedHandlerFaerie;
