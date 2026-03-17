"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.RolePlayEffect = void 0;
const AbilityEffect_1 = require("./AbilityEffect");
class RolePlayEffect extends AbilityEffect_1.AbilityEffect {
    constructor(source, description) {
        super('roleplay', source);
        this.description = description;
    }
}
exports.RolePlayEffect = RolePlayEffect;
