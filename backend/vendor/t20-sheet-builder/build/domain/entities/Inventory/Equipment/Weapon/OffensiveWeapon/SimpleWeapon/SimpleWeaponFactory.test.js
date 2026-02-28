"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
const EquipmentName_1 = require("../../../EquipmentName");
const Club_1 = require("./Club");
const Dagger_1 = require("./Dagger");
const SimpleWeaponFactory_1 = require("./SimpleWeaponFactory");
describe('EquipmentFactory', () => {
    it('should make a dagger from serialized', () => {
        const dagger = SimpleWeaponFactory_1.SimpleWeaponFactory.makeFromSerialized({
            name: EquipmentName_1.EquipmentName.dagger,
        });
        expect(dagger).toBeInstanceOf(Dagger_1.Dagger);
    });
    it('should make a club from serialized', () => {
        const club = SimpleWeaponFactory_1.SimpleWeaponFactory.makeFromSerialized({
            name: EquipmentName_1.EquipmentName.club,
        });
        expect(club).toBeInstanceOf(Club_1.Club);
    });
});
