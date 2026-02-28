"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.Weapon = void 0;
const Equipment_1 = require("../Equipment");
class Weapon extends Equipment_1.Equipment {
    constructor(proficiency) {
        super();
        this.proficiency = proficiency;
    }
}
exports.Weapon = Weapon;
