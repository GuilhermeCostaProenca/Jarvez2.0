"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.CharacterAppliedFightStyle = void 0;
class CharacterAppliedFightStyle {
    constructor(fightStyle, indexesToRemove) {
        this.fightStyle = fightStyle;
        this.indexesToRemove = indexesToRemove;
    }
    removeModifiers(modifiers) {
        var _a, _b;
        (_a = this.indexesToRemove.attack) === null || _a === void 0 ? void 0 : _a.contextual.forEach(index => {
            modifiers.attack.contextual.remove(index);
        });
        (_b = this.indexesToRemove.defense) === null || _b === void 0 ? void 0 : _b.contextual.forEach(index => {
            modifiers.defense.contextual.remove(index);
        });
    }
}
exports.CharacterAppliedFightStyle = CharacterAppliedFightStyle;
