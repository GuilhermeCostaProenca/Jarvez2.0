"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.AllihannaArmorEffect = void 0;
const Ability_1 = require("../../Ability");
const ManaCost_1 = require("../../ManaCost");
const RaceAbilityName_1 = require("../RaceAbilityName");
class AllihannaArmorEffect extends Ability_1.ActivateableAbilityEffect {
    constructor() {
        super({
            duration: 'scene',
            execution: 'moviment',
            source: RaceAbilityName_1.RaceAbilityName.allihannaArmor,
        });
        this.baseCosts = [new ManaCost_1.ManaCost(1)];
        this.description = 'Você pode gastar'
            + ' uma ação de movimento e 1 PM para transformar'
            + ' sua pele em casca de árvore, recebendo +2 na Defesa'
            + ' até o fim da cena.';
    }
}
exports.AllihannaArmorEffect = AllihannaArmorEffect;
