"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.ChurchMemberEffect = void 0;
const Ability_1 = require("../../Ability");
const OriginPowerName_1 = require("./OriginPowerName");
class ChurchMemberEffect extends Ability_1.RolePlayEffect {
    constructor() {
        super(OriginPowerName_1.OriginPowerName.churchMember, ChurchMemberEffect.description);
    }
}
exports.ChurchMemberEffect = ChurchMemberEffect;
ChurchMemberEffect.description = 'Você consegue hospedagem confortável e informação'
    + 'em qualquer templo de sua divindade, para você e seus aliados.';
