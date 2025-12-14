from server.app.utils.convert_measurement_to_format import short_format_measurement_ip, short_format_measurement_dn
from server.app.utils.validate import is_ip_address
from server.app.dtos.SearchRequest import SearchRequest
from sqlalchemy.orm import Session, Query
from sqlalchemy import and_, or_, exists
from typing import Optional, List
from datetime import datetime
from server.app.dtos.full_ntp_measurement import (
    FullMeasurementIP, FullMeasurementDN, 
    NTPv4Measurement, NTPv5Measurement,
    NTPv4ServerInfo, NTPv5ServerInfo,
    NTSMeasurement, NTPVersions, DNIPLink
)

def search_server(settings: SearchRequest, session: Session) -> list[dict]:
    """
    The main method that search through the database. The server can be empty.

    Args:
        settings (SearchRequest): The search request with filters.
        session (Session): The database session.

    Returns:
        list[dict]: List of DN or IP objects matching the search criteria.
    """
    if True == True: # work in progress.
        return []
    if settings.server == "":
        return search_domain_name(settings, session, True) + search_ip_address(settings, session, True)
    if is_ip_address(settings.server) is not None:
        return search_ip_address(settings, session)
    return search_domain_name(settings, session)


def search_domain_name(settings: SearchRequest, session: Session, skip_server_filter: bool=False) -> list[dict]:
    """
    Search for measurements by domain name using functional query building.
    We assume that settings.server is a domain name here.
    It returns "short format" data.

    Args:
        settings (SearchRequest): The search request with filters.
        session (Session): The database session.
        skip_server_filter (bool, optional): If True, skip filtering by server.

    Returns:
        list[dict]: List of FullMeasurementDN objects matching the search criteria.
    """
    query = session.query(FullMeasurementDN)
    if skip_server_filter == False:
        query = filter_by_dn(query, settings.server)
    # query = filter_by_measurement_type(query, settings.measurement_type)
    query = filter_by_wanted_ip_type(query, settings.wanted_ip_type)

    # execute the query
    ans_list = query.distinct().all()
    ans = []
    for m_dn in ans_list:
        ans.append(short_format_measurement_dn(session, m_dn))
    return ans


def search_ip_address(settings: SearchRequest, session: Session, skip_server_filter: bool=False) -> list[dict]:
    """
    Search for measurements by IP address using functional query building.
    We assume that settings.server is an IP address here.
    
    Args:
        settings (SearchRequest): The search request with filters.
        session (Session): The database session.
        skip_server_filter (bool, optional): If True, skip filtering by server.
        
    Returns:
        list[dict]: List of FullMeasurementIP objects matching the search criteria.
    """
    # Create base query
    query = session.query(FullMeasurementIP)
    if skip_server_filter == False:
        query = filter_by_ip(query, settings.server)
    query = filter_by_measurement_type(query, settings.measurement_type)
    # execute the query
    ans_list = query.distinct().all()
    ans = []
    for m_ip in ans_list:
        ans.append(short_format_measurement_ip(session, m_ip, known_server_dn=None))
    return ans

def filter_by_dn(query: Query, dn: Optional[str]) -> Query:
    """
    Filter by Domain Name.
    Args:
        query (Query): Query object.
        dn (Optional[str]): Domain name.
    Returns:
        Query: The updated query.
    """
    if dn and dn.strip():
        dn = dn.strip()
        query = query.filter_by(server=dn)
    return query

def filter_by_wanted_ip_type(query: Query, wanted_ip_type: Optional[int]) -> Query:
    """
    Filter by wanted_ip_type.
    Args:
        query (Query): Query object.
        wanted_ip_type (Optional[int]): wanted ip type (4 or 6).
    Returns:
        Query: The updated query.
    """
    if wanted_ip_type is not None:
        if wanted_ip_type == 4:
            # IPv4: filter DNs that have at least one IP measurement without colons
            subquery = exists().where(
                and_(
                    DNIPLink.id_dn == FullMeasurementDN.id_m_dn,
                    DNIPLink.id_ip == FullMeasurementIP.id_m_ip,
                    ~FullMeasurementIP.server_ip.contains(":")
                )
            )
            query = query.filter(subquery)
        elif wanted_ip_type == 6:
            # IPv6: filter DNs that have at least one IP measurement with colons
            subquery = exists().where(
                and_(
                    DNIPLink.id_dn == FullMeasurementDN.id_m_dn,
                    DNIPLink.id_ip == FullMeasurementIP.id_m_ip,
                    FullMeasurementIP.server_ip.contains(":")
                )
            )
            query = query.filter(subquery)
    return query

def filter_by_ip(query: Query, ip: Optional[str]) -> Query:
    """
    Filter by IP address.
    Args:
        query (Query): Query object.
        ip (Optional[str]): The IP address to filter by.
    Returns:
        Query: The updated query.
    """
    if ip and ip.strip():
        ip = ip.strip()
        query = query.filter_by(server_ip=ip)
    return query

def filter_by_measurement_type(query: Query, measurement_type: Optional[str]) -> Query:
    """
    Filter by measurement_type.
    Args:
        query (Query): Query object.
        measurement_type (Optional[str]): The measurement type (example: ntpv4).
    Returns:
        Query: The updated query.
    """
    if measurement_type and measurement_type.strip():
        measurement_type = measurement_type.strip()
        query = query.filter_by(response_version=measurement_type)
    return query