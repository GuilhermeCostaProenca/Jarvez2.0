"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.CharacterAttackTriggeredEffect = void 0;
class CharacterAttackTriggeredEffect {
    constructor(effect, modifiers) {
        this.effect = effect;
        this.modifiersIndexes = {};
        this.isEnabled = false;
        this.modifiers = {
            attack: modifiers.test,
            damage: modifiers.damage,
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
        var _a, _b, _c, _d;
        return {
            effect: this.effect.serialize(),
            modifiers: {
                attack: (_a = this.modifiers.attack) === null || _a === void 0 ? void 0 : _a.serialize(sheet, context),
                damage: (_b = this.modifiers.damage) === null || _b === void 0 ? void 0 : _b.serialize(sheet, context),
                skillExceptAttack: (_c = this.modifiers.skillExceptAttack) === null || _c === void 0 ? void 0 : _c.serialize(sheet, context),
                skill: (_d = this.modifiers.skill) === null || _d === void 0 ? void 0 : _d.serialize(sheet, context),
            },
        };
    }
}
exports.CharacterAttackTriggeredEffect = CharacterAttackTriggeredEffect;
