import { Critical } from '../../../../../Attack/Critical';
import { DiceRoll } from '../../../../../Dice/DiceRoll';
import { WeaponPurposeMelee } from '../../WeaponPurpose';
import { ExoticWeapon } from './ExoticWeapon';
import { type ExoticWeaponName } from './ExoticWeaponName';
export declare class DwarfAxe extends ExoticWeapon {
    static damage: DiceRoll;
    static critical: Critical;
    static equipmentName: ExoticWeaponName;
    static purposes: WeaponPurposeMelee[];
    static price: number;
    damage: DiceRoll;
    critical: Critical;
    name: ExoticWeaponName;
    purposes: WeaponPurposeMelee[];
    price: number;
}
