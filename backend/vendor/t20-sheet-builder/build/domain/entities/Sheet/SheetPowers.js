"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.SheetPowers = void 0;
class SheetPowers {
    constructor(powers = {
        general: new Map(),
        origin: new Map(),
        role: new Map(),
        granted: new Map(),
    }) {
        this.powers = powers;
    }
    pickGeneralPower(power, transaction, source) {
        power.addToSheet(transaction, source);
        this.powers.general.set(power.name, power);
    }
    pickRolePower(power, transaction, source) {
        power.addToSheet(transaction, source);
        this.powers.role.set(power.name, power);
    }
    pickOriginPower(power, transaction, source) {
        power.addToSheet(transaction, source);
        this.powers.origin.set(power.name, power);
    }
    pickGrantedPower(power, transaction, source) {
        power.addToSheet(transaction);
        this.powers.granted.set(power.name, power);
    }
    getGeneralPowers() {
        return this.powers.general;
    }
    getOriginPowers() {
        return this.powers.origin;
    }
    getRolePowers() {
        return this.powers.role;
    }
    getGrantedPowers() {
        return this.powers.granted;
    }
    serializeOriginPowers() {
        const originPowers = [];
        this.getOriginPowers().forEach(originPower => {
            originPowers.push(originPower.serialize());
        });
        return originPowers;
    }
    serializeGrantedPowers() {
        const grantedPowers = [];
        this.getGrantedPowers().forEach(grantedPower => {
            grantedPowers.push(grantedPower.serialize());
        });
        return grantedPowers;
    }
    serializeRolePowers() {
        const rolePowers = [];
        this.getRolePowers().forEach(rolePower => {
            rolePowers.push(rolePower.serialize());
        });
        return rolePowers;
    }
    serializeGeneralPowers() {
        const generalPowers = [];
        this.getGeneralPowers().forEach(generalPower => {
            generalPowers.push(generalPower.serialize());
        });
        return generalPowers;
    }
}
exports.SheetPowers = SheetPowers;
