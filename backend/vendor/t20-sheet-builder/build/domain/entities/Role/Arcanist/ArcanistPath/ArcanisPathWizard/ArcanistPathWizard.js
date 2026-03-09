"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.ArcanistPathWizard = void 0;
const AbilityEffects_1 = require("../../../../Ability/AbilityEffects");
const ArcanistPath_1 = require("../ArcanistPath");
const ArcanistPathWizardFocusEffect_1 = require("./ArcanistPathWizardFocusEffect");
class ArcanistPathWizard extends ArcanistPath_1.ArcanistPath {
    constructor(focus) {
        super();
        this.focus = focus;
        this.spellsAttribute = 'intelligence';
        this.spellLearnFrequency = 'all';
        this.pathName = ArcanistPath_1.ArcanistPathName.wizard;
        this.effects = new AbilityEffects_1.AbilityEffects({
            passive: {
                focus: new ArcanistPathWizardFocusEffect_1.ArcanistPathWizardFocusEffect(focus),
            },
        });
    }
    getFocus() {
        return this.effects.passive.focus.focus;
    }
    serializePath() {
        return {
            name: this.pathName,
            focus: this.focus.equipment.name,
        };
    }
}
exports.ArcanistPathWizard = ArcanistPathWizard;
