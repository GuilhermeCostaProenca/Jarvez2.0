import type { OffensiveWeapon } from '../Inventory/Equipment/Weapon/OffensiveWeapon/OffensiveWeapon';
import { type Attributes, type Attribute } from '../Sheet';
import { Attack } from './Attack';
export declare class WeaponAttack extends Attack {
    readonly weapon: OffensiveWeapon;
    private selectedPurposeIndex;
    constructor(weapon: OffensiveWeapon);
    getTestDefaultSkill(): import("..").SkillName;
    selectPurpose(index: number): void;
    getDamageAttribute(): keyof Attributes | undefined;
    getCustomTestAttributes(): Set<Attribute>;
}
