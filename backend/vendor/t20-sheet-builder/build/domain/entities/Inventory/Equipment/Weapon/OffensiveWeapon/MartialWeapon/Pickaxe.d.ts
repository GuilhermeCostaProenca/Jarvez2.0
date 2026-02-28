import { Critical } from '../../../../../Attack/Critical';
import { DiceRoll } from '../../../../../Dice/DiceRoll';
import { type WeaponPurpose, WeaponPurposeMelee } from '../../WeaponPurpose';
import { MartialWeapon } from './MartialWeapon';
import { type MartialWeaponName } from './MartialWeaponName';
export declare class Pickaxe extends MartialWeapon {
    static damage: DiceRoll;
    static critical: Critical;
    static equipmentName: MartialWeaponName;
    static purposes: WeaponPurposeMelee[];
    static price: number;
    damage: DiceRoll;
    critical: Critical;
    name: MartialWeaponName;
    purposes: WeaponPurpose[];
    price: number;
}
