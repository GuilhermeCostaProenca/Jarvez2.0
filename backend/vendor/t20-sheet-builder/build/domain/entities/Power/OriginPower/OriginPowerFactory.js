"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.OriginPowerFactory = void 0;
const errors_1 = require("../../../errors");
const ChurchMember_1 = require("./ChurchMember");
const OriginPowerName_1 = require("./OriginPowerName");
const SpecialFriend_1 = require("./SpecialFriend");
class OriginPowerFactory {
    static make(params) {
        if (params.power === OriginPowerName_1.OriginPowerName.churchMember) {
            return new ChurchMember_1.ChurchMember();
        }
        if (params.power === OriginPowerName_1.OriginPowerName.specialFriend) {
            if (!params.specialFriendSkill) {
                throw new errors_1.SheetBuilderError('MISSING_SPECIAL_FRIEND_SKILL');
            }
            return new SpecialFriend_1.SpecialFriend(params.specialFriendSkill);
        }
        throw new errors_1.SheetBuilderError('UNKNOWN_ORIGIN_POWER');
    }
}
exports.OriginPowerFactory = OriginPowerFactory;
OriginPowerFactory.map = {
    churchMember: ChurchMember_1.ChurchMember,
    specialFriend: SpecialFriend_1.SpecialFriend,
};
