import { type GrantedPower } from '../Power/GrantedPower/GrantedPower';
import { type GrantedPowerName } from '../Power/GrantedPower/GrantedPowerName';
import { type TransactionInterface } from '../Sheet/TransactionInterface';
import { type Deity } from './Deities';
export type SerializedDevotion = {
    deity: Deity;
    choosedPowers: GrantedPowerName[];
};
export declare class Devotion {
    readonly deity: Deity;
    private _choosedPowers;
    constructor(deity: Deity, _choosedPowers: GrantedPower[]);
    serialize(): SerializedDevotion;
    addPower(power: GrantedPower): void;
    removePower(powerName: GrantedPowerName): void;
    addToSheet(transaction: TransactionInterface): void;
    get choosedPowers(): GrantedPower[];
}
