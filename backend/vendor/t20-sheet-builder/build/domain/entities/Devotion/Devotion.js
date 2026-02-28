"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.Devotion = void 0;
const errors_1 = require("../../errors");
const PickGrantedPower_1 = require("../Action/PickGrantedPower");
class Devotion {
    constructor(deity, _choosedPowers) {
        this.deity = deity;
        this._choosedPowers = _choosedPowers;
    }
    serialize() {
        return {
            deity: this.deity,
            choosedPowers: this._choosedPowers.map(power => power.name),
        };
    }
    addPower(power) {
        this._choosedPowers.push(power);
    }
    removePower(powerName) {
        this._choosedPowers = this._choosedPowers.filter(power => power.name !== powerName);
    }
    addToSheet(transaction) {
        const sheetDevotion = transaction.sheet.getSheetDevotion();
        if (sheetDevotion.getGrantedPowerCount() !== this._choosedPowers.length) {
            throw new errors_1.SheetBuilderError('INVALID_POWER_COUNT');
        }
        if (this.deity.allowedToDevote !== 'all') {
            const isRaceAllowedToDevote = this.deity.allowedToDevote.races.includes(transaction.sheet.getSheetRace().getRace().name);
            const isRoleAllowedToDevote = this.deity.allowedToDevote.roles.includes(transaction.sheet.getSheetRole().getRole().name);
            if (!isRaceAllowedToDevote && !isRoleAllowedToDevote) {
                throw new errors_1.SheetBuilderError('NOT_ALLOWED_TO_DEVOTE');
            }
        }
        this._choosedPowers.forEach(power => {
            const isAllowed = this.deity.grantedPowers.includes(power.name);
            if (!isAllowed) {
                throw new errors_1.SheetBuilderError('NOT_ALLOWED_POWER');
            }
            transaction.run(new PickGrantedPower_1.PickGrantedPower({
                payload: {
                    power,
                    source: this.deity.name,
                },
                transaction,
            }));
        });
    }
    get choosedPowers() {
        return this._choosedPowers;
    }
}
exports.Devotion = Devotion;
