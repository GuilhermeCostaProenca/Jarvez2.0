"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.ArcanistFactory = void 0;
const Spell_1 = require("../../Spell");
const ArcanistBuider_1 = require("./ArcanistBuider");
const ArcanistPath_1 = require("./ArcanistPath");
const ArcanistPathSerializedHandler_1 = require("./ArcanistPath/ArcanistPathSerializedHandler");
class ArcanistFactory {
    static makeFromParams(params) {
        const sorcerer = new ArcanistPath_1.ArcanistPathHandlerSorcerer();
        const mage = new ArcanistPath_1.ArcanistPathHandlerMage();
        const wizard = new ArcanistPath_1.ArcanistPathHandlerWizard();
        sorcerer
            .setNext(mage)
            .setNext(wizard);
        return ArcanistBuider_1.ArcanistBuilder
            .chooseSkills(params.chosenSkills)
            .choosePath(sorcerer.execute(params))
            .chooseSpells(params.initialSpells.map(spellName => Spell_1.SpellFactory.make(spellName)));
    }
    static makeFromSerialized(serialized) {
        const sorcerer = new ArcanistPathSerializedHandler_1.ArcanistPathSerializedHandlerSorcerer();
        const mage = new ArcanistPathSerializedHandler_1.ArcanistPathSerializedHandlerMage();
        const wizard = new ArcanistPathSerializedHandler_1.ArcanistPathSerializedHandlerWizard();
        sorcerer
            .setNext(mage)
            .setNext(wizard);
        return ArcanistBuider_1.ArcanistBuilder
            .chooseSkills(serialized.selectedSkillsByGroup)
            .choosePath(sorcerer.execute(serialized.path))
            .chooseSpells(serialized.initialSpells.map(spellName => Spell_1.SpellFactory.make(spellName)));
    }
}
exports.ArcanistFactory = ArcanistFactory;
