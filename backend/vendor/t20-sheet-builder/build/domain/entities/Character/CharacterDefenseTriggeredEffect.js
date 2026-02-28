"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.CharacterDefenseTriggeredEffect = void 0;
class CharacterDefenseTriggeredEffect {
    constructor(effect, defenseModifiers) {
        this.effect = effect;
        this.modifiersIndexes = {};
        this.isEnabled = false;
        this.modifiers = {
            defense: defenseModifiers,
        };
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
            modifiersIndexes: this.modifiersIndexes,
            modifiers: this.modifiers,
        });
        this.isEnabled = false;
    }
    getIsEnabled() {
        return this.isEnabled;
    }
    getManaCost() {
        return this.manaCost;
    }
    serialize(sheet, context) {
        var _a;
        return {
            effect: this.effect.serialize(),
            modifiers: {
                defense: (_a = this.modifiers.defense) === null || _a === void 0 ? void 0 : _a.serialize(sheet, context),
            },
        };
    }
}
exports.CharacterDefenseTriggeredEffect = CharacterDefenseTriggeredEffect;
