"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.LinWuTraditionEffect = void 0;
const Ability_1 = require("../../../Ability");
const GrantedPowerName_1 = require("../GrantedPowerName");
class LinWuTraditionEffect extends Ability_1.RolePlayEffect {
    constructor() {
        super(GrantedPowerName_1.GrantedPowerName.linWuTradition, LinWuTraditionEffect.description);
    }
}
exports.LinWuTraditionEffect = LinWuTraditionEffect;
LinWuTraditionEffect.description = 'Você considera a katana uma arma simples e,'
    + ' se for proficiente em armas marciais, recebe +1 na'
    + ' margem de ameaça com ela.';
