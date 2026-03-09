import { Devotion } from '../Devotion/Devotion';
import type { Armor } from '../Inventory/Equipment/Weapon/DefensiveWeapon/Armor/Armor';
import type { MartialWeapon } from '../Inventory/Equipment/Weapon/OffensiveWeapon/MartialWeapon/MartialWeapon';
import type { SimpleWeapon } from '../Inventory/Equipment/Weapon/OffensiveWeapon/SimpleWeapon/SimpleWeapon';
import type { OriginInterface } from '../Origin/Origin';
import type { RaceInterface } from '../Race/RaceInterface';
import type { RoleInterface } from '../Role/RoleInterface';
import type { SkillName } from '../Skill/SkillName';
import type { Attributes } from './Attributes';
import { BuildingSheet } from './BuildingSheet/BuildingSheet';
import { CharacterSheet } from './CharacterSheet/CharacterSheet';
import { type SerializedSheetInterface } from './SerializedSheet';
export type SheetBuilderInitialEquipmentParams = {
    simpleWeapon: SimpleWeapon;
    martialWeapon?: MartialWeapon;
    armor?: Armor;
    money: number;
};
export type SheetBuilderInterface = {
    build(): CharacterSheet;
    reset(): SheetBuilder;
    addInitialEquipment(params: SheetBuilderInitialEquipmentParams): SheetBuilder;
    trainIntelligenceSkills(skills: SkillName[]): SheetBuilder;
    chooseOrigin(origin: OriginInterface): SheetBuilder;
    chooseRole(role: RoleInterface): SheetBuilder;
    chooseRace(race: RaceInterface): SheetBuilder;
};
export declare class SheetBuilder implements SheetBuilderInterface {
    private sheet;
    static makeFromSerialized(serialized: SerializedSheetInterface): CharacterSheet;
    constructor(sheet?: BuildingSheet);
    getBuildingSheet(): BuildingSheet;
    reset(sheet?: BuildingSheet): this;
    setInitialAttributes: (attributes: Attributes) => this;
    chooseRace(race: RaceInterface): this;
    chooseRole(role: RoleInterface): this;
    chooseOrigin(origin: OriginInterface): this;
    trainIntelligenceSkills(skills: SkillName[]): this;
    addInitialEquipment(params: {
        simpleWeapon: SimpleWeapon;
        martialWeapon?: MartialWeapon;
        armor?: Armor;
        money: number;
    }): this;
    addDevotion(devotion: Devotion): this;
    build(): CharacterSheet;
    private createSheet;
}
