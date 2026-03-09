"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.ArcanistLineageFaerie = void 0;
const AbilityEffects_1 = require("../../../../../../Ability/AbilityEffects");
const ArcanistLineage_1 = require("../ArcanistLineage");
const ArcanistLineageType_1 = require("../ArcanistLineageType");
const ArcanistLineageFaerieCheatTrainingEffect_1 = require("./ArcanistLineageFaerieCheatTrainingEffect");
const ArcanistLineageFaerieExtraSpellEffect_1 = require("./ArcanistLineageFaerieExtraSpellEffect");
class ArcanistLineageFaerie extends ArcanistLineage_1.ArcanistLineage {
    constructor(extraSpell) {
        super();
        this.type = ArcanistLineageType_1.ArcanistLineageType.faerie;
        this.effects = {
            basic: new AbilityEffects_1.AbilityEffects({
                passive: {
                    cheatTraining: new ArcanistLineageFaerieCheatTrainingEffect_1.ArcanistLineageFaerieCheatTrainingEffect(),
                    extraSpell: new ArcanistLineageFaerieExtraSpellEffect_1.ArcanistLineageFaerieExtraSpellEffect(extraSpell),
                },
            }),
            enhanced: new AbilityEffects_1.AbilityEffects(),
            higher: new AbilityEffects_1.AbilityEffects(),
        };
    }
    getExtraSpell() {
        return this.effects.basic.passive.extraSpell.spell;
    }
    serialize() {
        return {
            type: this.type,
            extraSpell: this.getExtraSpell().name,
        };
    }
}
exports.ArcanistLineageFaerie = ArcanistLineageFaerie;
