"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.ArcanistPathMage = void 0;
const AbilityEffects_1 = require("../../../../Ability/AbilityEffects");
const ArcanistPath_1 = require("../ArcanistPath");
const ArcanistPathMageExtraSpellEffect_1 = require("./ArcanistPathMageExtraSpellEffect");
class ArcanistPathMage extends ArcanistPath_1.ArcanistPath {
    constructor(additionalSpell) {
        super();
        this.spellsAttribute = 'intelligence';
        this.spellLearnFrequency = 'all';
        this.pathName = ArcanistPath_1.ArcanistPathName.mage;
        this.effects = new AbilityEffects_1.AbilityEffects({
            passive: {
                extraSpell: new ArcanistPathMageExtraSpellEffect_1.ArcanistPathMageExtraSpellEffect(additionalSpell),
            },
        });
    }
    getExtraSpell() {
        return this.effects.passive.extraSpell.spell;
    }
    serializePath() {
        return {
            name: this.pathName,
            extraSpell: this.getExtraSpell().name,
        };
    }
}
exports.ArcanistPathMage = ArcanistPathMage;
