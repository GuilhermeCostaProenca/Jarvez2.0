import { type GrantedPowerMap, type GeneralPowerMap, type OriginPowerMap, type RolePowerMap } from '../Map';
import { type GeneralPowerInterface } from '../Power/GeneralPower/GeneralPower';
import { type GrantedPower } from '../Power/GrantedPower/GrantedPower';
import { type OriginPowerInterface } from '../Power/OriginPower/OriginPower';
import { type RolePowerInterface } from '../Role/RolePower';
import { type TranslatableName } from '../Translator';
import { type SerializedSheetOriginPower, type SerializedSheetGrantedPower, type SerializedSheetRolePower, type SerializedSheetGeneralPower } from './SerializedSheet';
import { type SheetPowersInterface, type SheetPowersMap } from './SheetPowersInterface';
import { type TransactionInterface } from './TransactionInterface';
export declare class SheetPowers implements SheetPowersInterface {
    private readonly powers;
    constructor(powers?: SheetPowersMap);
    pickGeneralPower(power: GeneralPowerInterface, transaction: TransactionInterface, source: TranslatableName): void;
    pickRolePower(power: RolePowerInterface, transaction: TransactionInterface, source: TranslatableName): void;
    pickOriginPower(power: OriginPowerInterface, transaction: TransactionInterface, source: TranslatableName): void;
    pickGrantedPower(power: GrantedPower, transaction: TransactionInterface, source: TranslatableName): void;
    getGeneralPowers(): GeneralPowerMap;
    getOriginPowers(): OriginPowerMap;
    getRolePowers(): RolePowerMap;
    getGrantedPowers(): GrantedPowerMap;
    serializeOriginPowers(): SerializedSheetOriginPower[];
    serializeGrantedPowers(): SerializedSheetGrantedPower[];
    serializeRolePowers(): SerializedSheetRolePower[];
    serializeGeneralPowers(): SerializedSheetGeneralPower[];
}
