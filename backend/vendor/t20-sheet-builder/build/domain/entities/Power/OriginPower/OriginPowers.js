"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.OriginPowers = void 0;
const ChurchMember_1 = require("./ChurchMember");
const SpecialFriend_1 = require("./SpecialFriend");
class OriginPowers {
    static getAll() {
        return Object.values(this.map);
    }
}
exports.OriginPowers = OriginPowers;
OriginPowers.map = {
    churchMember: ChurchMember_1.ChurchMember,
    specialFriend: SpecialFriend_1.SpecialFriend,
};
