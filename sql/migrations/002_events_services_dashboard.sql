-- Revision 002_events_services_dashboard
-- New tables (event_types, event_series, event_occurrences, service_plan_items,
-- dashboard_layouts) are created from the SQLAlchemy models by the same revision.
-- Group meeting columns are kept, unused: events linked to a group now hold its schedule.
-- Every statement is safe to run again. Nothing is dropped.

COMMENT ON COLUMN groups.meeting_day IS 'Unused since 002. A group schedule lives on its linked event series.';
COMMENT ON COLUMN groups.meeting_frequency IS 'Unused since 002. A group schedule lives on its linked event series.';
COMMENT ON COLUMN groups.meeting_start_time IS 'Unused since 002. A group schedule lives on its linked event series.';
COMMENT ON COLUMN groups.meeting_end_time IS 'Unused since 002. A group schedule lives on its linked event series.';
COMMENT ON COLUMN groups.meeting_location IS 'Unused since 002. A group schedule lives on its linked event series.';
COMMENT ON COLUMN groups.meeting_address_id IS 'Unused since 002. A group schedule lives on its linked event series.';
COMMENT ON COLUMN groups.meeting_notes IS 'Unused since 002. A group schedule lives on its linked event series.';
