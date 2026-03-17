"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.Spell = void 0;
const Ability_1 = require("../Ability/Ability");
const SpellCircleManaCost_1 = require("./SpellCircleManaCost");
const SpellCost_1 = require("./SpellCost");
class Spell extends Ability_1.Ability {
    constructor(name, circle, type) {
        super(name, 'spell');
        this.name = name;
        this.circle = circle;
        this.type = type;
        this.cost = new SpellCost_1.SpellCost(this.circle);
    }
}
exports.Spell = Spell;
Spell.circleManaCost = SpellCircleManaCost_1.circleManaCost;
