"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.CharacterSkillTriggeredEffect = void 0;
class CharacterSkillTriggeredEffect {
    constructor(effect, modifiers) {
        this.effect = effect;
        this.modifiers = modifiers;
        this.modifiersIndexes = {};
        this.isEnabled = false;
    }
    enable(activation) {
        const { manaCost } = this.effect.enable({
            modifiersIndexes: this.modifiersIndexes,
            modifiers: this.modifiers,
        }, activation);
        if (manaCost) {
            this.manaCost = manaCost;
        }
        this.isEnabled = true;
    }
    disable() {
        this.effect.disable({
            modifiers: this.modifiers,
            modifiersIndexes: this.modifiersIndexes,
        });
        this.isEnabled = false;
    }
    getIsEnabled() {
        return this.isEnabled;
    }
    getManaCost() {
        return this.manaCost;
    }
}
exports.CharacterSkillTriggeredEffect = CharacterSkillTriggeredEffect;
